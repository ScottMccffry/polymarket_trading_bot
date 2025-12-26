export default function Settings() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-white mb-6">Settings</h1>
      <div className="space-y-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">API Configuration</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                API Endpoint
              </label>
              <input
                type="text"
                className="w-full bg-gray-700 border border-gray-600 rounded-md px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="http://localhost:8000"
              />
            </div>
          </div>
        </div>
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Trading Settings</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Paper Trading Mode</span>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm">
                Enabled
              </button>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Auto-execute Signals</span>
              <button className="bg-gray-600 text-white px-4 py-2 rounded-md text-sm">
                Disabled
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
