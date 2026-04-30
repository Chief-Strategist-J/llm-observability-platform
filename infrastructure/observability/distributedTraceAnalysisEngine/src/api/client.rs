use crate::domain::events::AnalysisResult;
use crate::domain::trace::{Span, Trace};
use reqwest::Client;
use serde::de::DeserializeOwned;

pub struct TraceAnalysisClient {
    client: Client,
    base_url: String,
}

#[derive(Debug, thiserror::Error)]
pub enum ClientError {
    #[error("request failed: {0}")]
    RequestFailed(#[from] reqwest::Error),
    #[error("server error: {status} - {body}")]
    ServerError { status: u16, body: String },
}

#[derive(serde::Deserialize)]
struct IngestResponse {
    accepted: usize,
    message: String,
}

#[derive(serde::Deserialize)]
struct FlushResponse {
    complete_traces: usize,
    partial_traces: usize,
    analysis_results: usize,
}

#[derive(serde::Deserialize)]
struct AnalysisResultsResponse {
    results: Vec<AnalysisResult>,
}

#[derive(serde::Deserialize)]
struct HealthResponse {
    status: String,
    version: String,
}

pub struct FlushResult {
    pub complete_traces: usize,
    pub partial_traces: usize,
    pub analysis_results: usize,
}

impl TraceAnalysisClient {
    pub fn new(base_url: &str) -> Self {
        Self {
            client: Client::new(),
            base_url: base_url.trim_end_matches('/').to_string(),
        }
    }

    pub async fn health(&self) -> Result<(String, String), ClientError> {
        let resp: HealthResponse = self.get("/health").await?;
        Ok((resp.status, resp.version))
    }

    pub async fn ingest_spans(&self, spans: &[Span]) -> Result<usize, ClientError> {
        let resp: IngestResponse = self.post("/api/v1/spans", spans).await?;
        Ok(resp.accepted)
    }

    pub async fn ingest_otlp(&self, payload: &serde_json::Value) -> Result<usize, ClientError> {
        let resp: IngestResponse = self.post("/api/v1/spans/otlp", payload).await?;
        Ok(resp.accepted)
    }

    pub async fn flush(&self) -> Result<FlushResult, ClientError> {
        let resp: FlushResponse = self.post_empty("/api/v1/flush").await?;
        Ok(FlushResult {
            complete_traces: resp.complete_traces,
            partial_traces: resp.partial_traces,
            analysis_results: resp.analysis_results,
        })
    }

    pub async fn get_results(&self) -> Result<Vec<AnalysisResult>, ClientError> {
        let resp: AnalysisResultsResponse = self.get("/api/v1/analysis/results").await?;
        Ok(resp.results)
    }

    pub async fn get_results_filtered(
        &self,
        limit: Option<usize>,
        offset: Option<usize>,
        trace_id: Option<&str>,
    ) -> Result<Vec<AnalysisResult>, ClientError> {
        let mut params = Vec::new();
        if let Some(limit) = limit {
            params.push(format!("limit={limit}"));
        }
        if let Some(offset) = offset {
            params.push(format!("offset={offset}"));
        }
        if let Some(trace_id) = trace_id {
            let encoded_trace_id = trace_id.replace(' ', "%20");
            params.push(format!("trace_id={encoded_trace_id}"));
        }

        let path = if params.is_empty() {
            "/api/v1/analysis/results".to_string()
        } else {
            format!("/api/v1/analysis/results?{}", params.join("&"))
        };

        let resp: AnalysisResultsResponse = self.get(&path).await?;
        Ok(resp.results)
    }

    pub async fn get_result(&self, trace_id: &str) -> Result<AnalysisResult, ClientError> {
        let path = format!("/api/v1/analysis/results/{}", trace_id);
        self.get(&path).await
    }

    pub async fn list_traces(&self) -> Result<Vec<serde_json::Value>, ClientError> {
        self.get("/api/v1/traces").await
    }

    pub async fn get_trace(&self, trace_id: &str) -> Result<Trace, ClientError> {
        let path = format!("/api/v1/traces/{}", trace_id);
        self.get(&path).await
    }

    async fn get<T: DeserializeOwned>(&self, path: &str) -> Result<T, ClientError> {
        let url = format!("{}{}", self.base_url, path);
        let response = self.client.get(&url).send().await?;
        let status = response.status();
        if !status.is_success() {
            let body = response.text().await.unwrap_or_default();
            return Err(ClientError::ServerError {
                status: status.as_u16(),
                body,
            });
        }
        Ok(response.json().await?)
    }

    async fn post<T: DeserializeOwned, B: serde::Serialize + ?Sized>(
        &self,
        path: &str,
        body: &B,
    ) -> Result<T, ClientError> {
        let url = format!("{}{}", self.base_url, path);
        let response = self.client.post(&url).json(body).send().await?;
        let status = response.status();
        if !status.is_success() {
            let body = response.text().await.unwrap_or_default();
            return Err(ClientError::ServerError {
                status: status.as_u16(),
                body,
            });
        }
        Ok(response.json().await?)
    }

    async fn post_empty<T: DeserializeOwned>(&self, path: &str) -> Result<T, ClientError> {
        let url = format!("{}{}", self.base_url, path);
        let response = self.client.post(&url).send().await?;
        let status = response.status();
        if !status.is_success() {
            let body = response.text().await.unwrap_or_default();
            return Err(ClientError::ServerError {
                status: status.as_u16(),
                body,
            });
        }
        Ok(response.json().await?)
    }
}
