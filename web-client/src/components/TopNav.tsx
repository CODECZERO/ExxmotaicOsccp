export default function TopNav() {
  return (
    <header className="fixed top-0 right-0 w-[calc(100%-16rem)] h-16 bg-white/80 backdrop-blur-md border-b border-slate-100 z-10 flex justify-between items-center px-8">
      <div className="flex items-center bg-surface-container-low px-4 py-2 rounded-full w-96">
        <span className="material-symbols-outlined text-outline text-xl">search</span>
        <input className="bg-transparent border-none focus:ring-0 text-sm w-full font-body outline-none" placeholder="Search sessions or chargers..." type="text"/>
      </div>
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 text-secondary font-bold text-sm bg-secondary/10 px-3 py-1.5 rounded-full">
          <span className="material-symbols-outlined text-lg">verified_user</span>
          System Status
        </div>
        <div className="flex items-center gap-3">
          <button className="hover:bg-slate-50 rounded-full p-2 text-on-surface-variant transition-all cursor-pointer">
            <span className="material-symbols-outlined">notifications</span>
          </button>
          <button className="hover:bg-slate-50 rounded-full p-2 text-on-surface-variant transition-all cursor-pointer">
            <span className="material-symbols-outlined">account_circle</span>
          </button>
          <button className="hover:bg-slate-50 rounded-full p-2 text-on-surface-variant transition-all cursor-pointer">
            <span className="material-symbols-outlined">power_settings_new</span>
          </button>
        </div>
      </div>
    </header>
  );
}
