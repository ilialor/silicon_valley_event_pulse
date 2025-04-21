// src/components/Calendar.jsx
import React from 'react';
import { Calendar as BigCalendar, dateFnsLocalizer } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import { useEvents } from '../hooks/useEvents.jsx';
import 'react-big-calendar/lib/css/react-big-calendar.css';

import { enUS } from 'date-fns/locale';

const locales = {
  'en-US': enUS,
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

function Calendar({ onEventClick }) {
  const { events, loading } = useEvents();

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const eventStyleGetter = (event) => {
    const style = {
      backgroundColor: event.source === 'Meetup' ? '#3788d8' :
                      event.source === 'Eventbrite' ? '#28a745' :
                      event.source === 'LinkedIn' ? '#0a66c2' : '#6c757d',
      borderRadius: '4px',
      opacity: 0.8,
      color: 'white',
      border: '0px',
      display: 'block'
    };
    return { style };
  };

  return (
    <div className="h-[600px]">
      <BigCalendar
        localizer={localizer}
        events={events}
        startAccessor="start"
        endAccessor="end"
        style={{ height: '100%' }}
        eventPropGetter={eventStyleGetter}
        onSelectEvent={onEventClick}
        views={['month', 'week', 'day']}
      />
    </div>
  );
}

export default Calendar;