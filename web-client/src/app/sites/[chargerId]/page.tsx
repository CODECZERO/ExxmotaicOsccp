import ChargerDetailClient from '@/components/charger/ChargerDetailClient';

export default async function ChargerDetailPage({
  params,
}: {
  params: Promise<{ chargerId: string }>;
}) {
  const { chargerId } = await params;

  return <ChargerDetailClient chargerId={chargerId} />;
}
