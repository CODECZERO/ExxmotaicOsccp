interface KeyValueItem {
  label: string;
  value: string;
}

interface KeyValueGridProps {
  items: KeyValueItem[];
}

export default function KeyValueGrid({ items }: KeyValueGridProps) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      {items.map((item) => (
        <div key={item.label} className="rounded-2xl border border-surface-container bg-surface-container-lowest p-4">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">{item.label}</p>
          <p className="mt-2 break-words text-sm font-semibold text-primary">{item.value}</p>
        </div>
      ))}
    </div>
  );
}
