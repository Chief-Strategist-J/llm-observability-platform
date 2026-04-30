export default function TestPage() {
  return (
    <div style={{ padding: 20, background: '#f0f0f0', minHeight: '100vh' }}>
      <h1>Simple Test Page</h1>
      <p>If you can see this, the basic React setup is working!</p>
      <p>
        Current URL:{' '}
        {typeof window !== 'undefined'
          ? window.location.href
          : 'Server-side rendering'}
      </p>
    </div>
  );
}
