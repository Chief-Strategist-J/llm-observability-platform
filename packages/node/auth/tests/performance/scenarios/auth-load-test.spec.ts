export const options = {
  stages: [
    { duration: '10s', target: 20 },
    { duration: '30s', target: 50 },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<200', 'p(99)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const baseUrl = __ENV.BASE_URL || 'http://localhost:3001';
  const timestamp = Date.now() + '_' + Math.floor(Math.random() * 10000);
  
  const signUpPayload = JSON.stringify({
    email: `perf_${timestamp}@test.com`,
    password: 'StrongPass123!',
    name: `Perf User ${timestamp}`,
    organization_name: `Perf Org ${timestamp}`,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  http.post(`${baseUrl}/api/v1/auth/sign-up`, signUpPayload, params);
}
