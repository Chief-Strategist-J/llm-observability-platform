//! # tracep
//!
//! Fire-and-forget OTel-wrapping tracer SDK for Rust.
//!
//! ## Quick start
//!
//! ```rust,no_run
//! use tracep::Tracer;
//!
//! #[tokio::main]
//! async fn main() {
//!     let tracer = Tracer::new(
//!         "http://localhost:4318",
//!         "my-api-key",
//!         "my-service",
//!     ).unwrap();
//!
//!     let tid = tracer.start("my-operation");
//!     tracer.trace(&tid, "MyClass", "my_fn", "step-1", "doing work", None, None);
//!     tracer.end(&tid, "ok");
//!     tracer.close();
//! }
//! ```

pub mod tracer;

pub use tracer::Tracer;
