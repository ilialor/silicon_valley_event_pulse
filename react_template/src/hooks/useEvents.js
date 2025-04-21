// src/hooks/useEvents.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';

const EventsContext = createContext();

export function EventsProvider({ children }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSources, setSelectedSources] = useState(['Meetup', 'Eventbrite', 'LinkedIn']);
  const [sources] = useState(['Meetup', 'Eventbrite', 'LinkedIn']);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        // TODO: Replace with actual API call to your backend
        const response = await fetch('/api/events');
        const data = await response.json();
        setEvents(data);
      } catch (error) {
        console.error('Error fetching events:', error);
        // Using mock data for demonstration
        setEvents([
          {
            id: 1,
            title: 'Tech Meetup',
            start: new Date(2024, 3, 15, 18, 0),
            end: new Date(2024, 3, 15, 20, 0),
            location: 'San Jose Convention Center',
            description: 'Monthly tech meetup in Silicon Valley',
            source: 'Meetup'
          },
          {
            id: 2,
            title: 'Startup Pitch Night',
            start: new Date(2024, 3, 16, 19, 0),
            end: new Date(2024, 3, 16, 21, 0),
            location: 'Palo Alto',
            description: 'Pitch your startup idea',
            source: 'Eventbrite'
          }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, []);

  const filteredEvents = events.filter(event => {
    const matchesSearch = searchTerm === '' || 
      event.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      event.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
      event.description.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesSource = selectedSources.includes(event.source);

    return matchesSearch && matchesSource;
  });

  return (
    <EventsContext.Provider
      value={{
        events: filteredEvents,
        loading,
        searchTerm,
        setSearchTerm,
        selectedSources,
        setSelectedSources,
        sources
      }}
    >
      {children}
    </EventsContext.Provider>
  );
}

export function useEvents() {
  const context = useContext(EventsContext);
  if (!context) {
    throw new Error('useEvents must be used within an EventsProvider');
  }
  return context;
}