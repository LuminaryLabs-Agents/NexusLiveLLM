export function createEventBus() {
  const events = [];
  return {
    emit(type, payload = {}) { const event = { type, payload, eventId: `${type}:${events.length}:${payload.commandId ?? "event"}` }; events.push(event); return event; },
    read(type) { return events.filter((event) => event.type === type); },
    readAll() { return events.slice(); },
    recent(limit = 48) { return events.slice(-limit); },
    clear() { events.length = 0; }
  };
}
