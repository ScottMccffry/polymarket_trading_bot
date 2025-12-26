export default function Statistics() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-white mb-6">Statistics</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-300 mb-4">Performance Overview</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Total Trades</span>
              <span className="text-white">0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Win Rate</span>
              <span className="text-white">0%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Avg. Return</span>
              <span className="text-white">0%</span>
            </div>
          </div>
        </div>
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-300 mb-4">Risk Metrics</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Sharpe Ratio</span>
              <span className="text-white">-</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Max Drawdown</span>
              <span className="text-white">0%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Volatility</span>
              <span className="text-white">-</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
