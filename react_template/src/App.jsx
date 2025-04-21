// src/App.jsx
import React, { useState } from 'react';
import Calendar from './components/Calendar';
import EventDetails from './components/EventDetails';
import Filter from './components/Filter';
import { EventsProvider } from './hooks/useEvents';

function App() {
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  const handleEventClick = (event) => {
    setSelectedEvent(event);
    setIsDetailsOpen(true);
  };

  return (
    <EventsProvider>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            <h1 className="text-3xl font-bold text-gray-900">
              Silicon Valley Events Calendar
            </h1>
          </div>
        </header>

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Filter />
          <div className="mt-6 bg-white shadow rounded-lg p-4">
            <Calendar onEventClick={handleEventClick} />
          </div>

          <EventDetails 
            event={selectedEvent}
            isOpen={isDetailsOpen}
            onClose={() => setIsDetailsOpen(false)}
          />
        </main>
      </div>
    </EventsProvider>
  );
}

export default App;