export function timeSince(then, now = null) {
  now = now !== null ? now : Date.now();
  var difference = then < now ? now - then : 0;
  const result = {
    weeks: 0,
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
  };

  result.weeks = Math.floor(difference / 1000 / 60 / 60 / 24 / 7);
  difference -= result.weeks * (1000 * 60 * 60 * 24 * 7);
  result.days = Math.floor(difference / 1000 / 60 / 60 / 24);
  difference -= result.days * 1000 * 60 * 60 * 24;
  result.hours = Math.floor(difference / 1000 / 60 / 60);
  difference -= result.hours * 1000 * 60 * 60;
  result.minutes = Math.floor(difference / 1000 / 60);
  difference -= result.minutes * 1000 * 60;
  result.seconds = Math.floor(difference / 1000);
  return result;
}

export function formatTimeSince(then, now = null) {
  const ages = timeSince(then, now);
  return ages.weeks > 0
    ? `${ages.weeks} week${ages.weeks > 1 ? "s" : ""} ago`
    : ages.days > 0
    ? `${ages.days} day${ages.days > 1 ? "s" : ""} ago`
    : ages.hours > 0
    ? `${ages.hours} hour${ages.hours > 1 ? "s" : ""} ago`
    : ages.minutes > 0
    ? `${ages.minutes} min${ages.minutes > 1 ? "s" : ""} ago`
    : `Just now`;
}
