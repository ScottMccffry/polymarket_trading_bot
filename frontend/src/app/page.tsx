export default function Dashboard() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-white mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-300 mb-2">Portfolio Value</h2>
          <p className="text-2xl font-bold text-white">$0.00</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-300 mb-2">Active Positions</h2>
          <p className="text-2xl font-bold text-white">0</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-300 mb-2">Today&apos;s P&L</h2>
          <p className="text-2xl font-bold text-white">$0.00</p>
        </div>
      </div>
    </div>
  );
}
