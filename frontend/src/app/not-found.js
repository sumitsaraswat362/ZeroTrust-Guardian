import Link from 'next/link';

export default function NotFound() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', textAlign: 'center' }}>
      <div style={{ fontSize: '72px', marginBottom: '16px' }}>404</div>
      <h2 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '12px' }}>Page Not Found</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', maxWidth: '400px' }}>
        The page you are looking for doesn't exist or has been moved.
      </p>
      <Link href="/" className="btn btn-primary">
        Return to Dashboard
      </Link>
    </div>
  );
}
