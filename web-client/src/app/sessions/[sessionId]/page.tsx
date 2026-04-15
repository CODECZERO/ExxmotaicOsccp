import SessionDetailClient from '@/components/session/SessionDetailClient';

export default async function SessionDetailPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = await params;

  return <SessionDetailClient sessionId={sessionId} />;
}
