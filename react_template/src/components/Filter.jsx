// src/components/Filter.jsx
import React from 'react';
import { useEvents } from '../hooks/useEvents';

function Filter() {
  const { 
    searchTerm,
    setSearchTerm,
    selectedSources,
    setSelectedSources,
    sources 
  } = useEvents();

  return (
    <div className="bg-white shadow rounded-lg p-4 mb-6">
      <div className="space-y-4">
        <div>
          <label htmlFor="search" className="block text-sm font-medium text-gray-700">
            Search Events
          </label>
          <input
            type="text"
            id="search"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            placeholder="Search by title, location, or description"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Event Sources
          </label>
          <div className="flex flex-wrap gap-2">
            {sources.map((source) => (
              <button
                key={source}
                onClick={() => {
                  setSelectedSources(prev =>
                    prev.includes(source)
                      ? prev.filter(s => s !== source)
                      : [...prev, source]
                  );
                }}
                className={`px-3 py-1 rounded-full text-sm font-medium ${
                  selectedSources.includes(source)
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {source}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Filter;