import * as fs from 'fs';
import * as path from 'path';

describe('Auth OpenAPI Contract Compliance', () => {
  it('should verify contracts/openapi/v1.yaml exists and is non-empty', () => {
    const contractPath = path.join(__dirname, '../../contracts/openapi/v1.yaml');
    expect(fs.existsSync(contractPath)).toBe(true);

    const content = fs.readFileSync(contractPath, 'utf8');
    expect(content).toContain('openapi: 3.0.3');
    expect(content).toContain('/api/v1/auth/login');
    expect(content).toContain('/api/v1/auth/keys');
  });
});
