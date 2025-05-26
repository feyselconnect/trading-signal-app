import React, { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Tab } from '@headlessui/react';
import { ArrowPathIcon } from '@heroicons/react/24/outline';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

// Initialize Supabase client
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || '';
const supabaseKey = process.env.REACT_APP_SUPABASE_ANON_KEY || '';
const supabase = createClient(supabaseUrl, supabaseKey);

// Types
interface MarketData {
  timestamp: string;
  asset: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface TradeSignal {
  asset: string;
  timeframe: string;
  bias: string;
  liquidity_zones: {
    clusters: {
      highs: number[];
      lows: number[];
    };
    pd_arrays: {
      premium: number;
      equilibrium: number;
      discount: number;
    };
  };
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  invalidation_point: number;
  system: string;
}

interface PortfolioMetrics {
  risk_reward_ratio: number;
  win_rate: number;
  drawdown: number;
}

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

function App() {
  // State
  const [accountBalance, setAccountBalance] = useState(10000);
  const [riskPercentage, setRiskPercentage] = useState(1);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1m');
  const [marketData, setMarketData] = useState<Record<string, MarketData[]>>({});
  const [signals, setSignals] = useState<TradeSignal[]>([]);
  const [metrics, setMetrics] = useState<Record<string, PortfolioMetrics>>({});
  const [loading, setLoading] = useState(false);

  // Timeframes
  const timeframes = ['1m', '5m', '15m', '1h', '4h', '1d'];
  const assets = ['XAUUSD', 'NASDAQ'];

  // Fetch data
  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch market data
      const { data: marketDataResponse } = await supabase
        .from('market_data')
        .select('*')
        .order('timestamp', { ascending: true });

      // Fetch trade signals
      const { data: signalsResponse } = await supabase
        .from('trade_signals')
        .select('*')
        .order('timestamp', { ascending: false });

      // Fetch portfolio metrics
      const { data: metricsResponse } = await supabase
        .from('portfolio_metrics')
        .select('*');

      // Process market data
      const processedMarketData: Record<string, MarketData[]> = {};
      assets.forEach(asset => {
        processedMarketData[asset] = marketDataResponse?.filter(
          (d: MarketData) => d.asset === asset
        ) || [];
      });

      setMarketData(processedMarketData);
      setSignals(signalsResponse || []);
      setMetrics(metricsResponse || {});
    } catch (error) {
      console.error('Error fetching data:', error);
    }
    setLoading(false);
  };

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, []);

  // Chart options
  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Price Chart',
      },
    },
    scales: {
      y: {
        beginAtZero: false,
      },
    },
  };

  // Render chart data
  const getChartData = (asset: string) => {
    const data = marketData[asset] || [];
    return {
      labels: data.map(d => new Date(d.timestamp).toLocaleTimeString()),
      datasets: [
        {
          label: asset,
          data: data.map(d => d.close),
          borderColor: 'rgb(75, 192, 192)',
          tension: 0.1,
        },
      ],
    };
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="px-4 py-6 sm:px-0">
          <h1 className="text-3xl font-bold text-gray-900">Trading Signal Dashboard</h1>
        </div>

        {/* User Inputs */}
        <div className="bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6 mb-6">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
            <div>
              <label className="block text-sm font-medium text-gray-700">Account Balance</label>
              <input
                type="number"
                value={accountBalance}
                onChange={(e) => setAccountBalance(Number(e.target.value))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Risk Percentage</label>
              <input
                type="number"
                min="1"
                max="2"
                step="0.1"
                value={riskPercentage}
                onChange={(e) => setRiskPercentage(Number(e.target.value))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Timeframe</label>
              <select
                value={selectedTimeframe}
                onChange={(e) => setSelectedTimeframe(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              >
                {timeframes.map(tf => (
                  <option key={tf} value={tf}>{tf}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="bg-white shadow sm:rounded-lg mb-6">
          <Tab.Group>
            <Tab.List className="flex space-x-1 rounded-t-lg bg-gray-100 p-1">
              {assets.map((asset) => (
                <Tab
                  key={asset}
                  className={({ selected }) =>
                    classNames(
                      'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                      'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                      selected
                        ? 'bg-white shadow text-blue-700'
                        : 'text-gray-600 hover:bg-white/[0.12] hover:text-gray-800'
                    )
                  }
                >
                  {asset}
                </Tab>
              ))}
            </Tab.List>
            <Tab.Panels className="p-4">
              {assets.map((asset) => (
                <Tab.Panel key={asset}>
                  <Line options={chartOptions} data={getChartData(asset)} />
                </Tab.Panel>
              ))}
            </Tab.Panels>
          </Tab.Group>
        </div>

        {/* Signals and Metrics */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Signals */}
          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg font-medium leading-6 text-gray-900">Recent Signals</h3>
              <div className="mt-4 space-y-4">
                {signals
                  .filter(signal => signal.timeframe === selectedTimeframe)
                  .map((signal, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex justify-between">
                        <div>
                          <p className="font-medium">{signal.asset}</p>
                          <p className="text-sm text-gray-500">{signal.system}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium">Entry: {signal.entry_price}</p>
                          <p className="text-sm text-gray-500">
                            SL: {signal.stop_loss} | TP: {signal.take_profit}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>

          {/* Metrics */}
          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg font-medium leading-6 text-gray-900">Portfolio Metrics</h3>
              <div className="mt-4 grid grid-cols-2 gap-4">
                {Object.entries(metrics).map(([timeframe, metric]) => (
                  <div key={timeframe} className="border rounded-lg p-4">
                    <p className="font-medium">{timeframe}</p>
                    <p className="text-sm">Win Rate: {(metric.win_rate * 100).toFixed(1)}%</p>
                    <p className="text-sm">R:R Ratio: {metric.risk_reward_ratio.toFixed(2)}</p>
                    <p className="text-sm">Drawdown: {(metric.drawdown * 100).toFixed(1)}%</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Refresh Button */}
        <div className="mt-6 flex justify-center">
          <button
            onClick={fetchData}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <ArrowPathIcon className={`h-5 w-5 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh Data
          </button>
        </div>
      </div>
    </div>
  );
}

export default App; 