"use client";

import { useEffect, useState } from "react";

type City = {
  name: string;
  timeZone: string;
  /** The team's own city: semibold time and the live dot. */
  home?: boolean;
  /** The Figma sample moment (2026-11-10 01:41 UTC), shown until the live time is known. */
  sample: { time: string; note: string };
};

const cities: City[] = [
  { name: "Manila", timeZone: "Asia/Manila", home: true, sample: { time: "9:41 am", note: "Our team" } },
  { name: "Sydney", timeZone: "Australia/Sydney", sample: { time: "12:41 pm", note: "3 hours ahead" } },
  { name: "New York", timeZone: "America/New_York", sample: { time: "8:41 pm", note: "Yesterday, 13 hours behind" } },
  { name: "London", timeZone: "Europe/London", sample: { time: "1:41 am", note: "8 hours behind" } },
];

const homeZone = "Asia/Manila";

/**
 * The time-zone row with live clocks. The server renders the Figma sample moment; once the page runs in the browser
 * it switches to the real time in each city and updates on the minute. The time is read only in the browser, never
 * while the page is prerendered.
 */
export function LiveTimeZones() {
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    let interval: number | undefined;
    const tick = () => setNow(new Date());
    tick();
    // Wait for the next minute boundary, then update every minute.
    const timeout = window.setTimeout(() => {
      tick();
      interval = window.setInterval(tick, 60_000);
    }, 60_000 - (Date.now() % 60_000));
    // Catch up straight away when the tab comes back into view.
    const onVisible = () => {
      if (document.visibilityState === "visible") tick();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.clearTimeout(timeout);
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, []);

  return (
    <>
      <ul className="aap-timezones" data-reveal-group>
        {cities.map((city) => {
          const live = now ? describe(city, now) : city.sample;
          return (
            <li
              key={city.name}
              className="aap-timezones__city"
              aria-current={city.home ? "true" : undefined}
              data-reveal-item
            >
              <span className="aap-timezones__name">{city.name}</span>
              <span className="aap-timezones__time">{live.time}</span>
              <span className="aap-timezones__note">{live.note}</span>
            </li>
          );
        })}
      </ul>
      <p className="text-caption text-ink-tertiary">
        {now ? "Live times in each city." : "Sample times for a November morning in Manila."}
      </p>
    </>
  );
}

/** Local time as "9:41 am", and how far ahead or behind Manila the city is. */
function describe(city: City, now: Date) {
  const local = zonedParts(now, city.timeZone);
  const time = `${local.hour12}:${String(local.minute).padStart(2, "0")} ${local.dayPeriod}`;
  if (city.home) return { time, note: city.sample.note };

  const home = zonedParts(now, homeZone);
  const hours = Math.round((local.offsetMinutes - home.offsetMinutes) / 6) / 10;
  const amount = `${Math.abs(hours)} ${Math.abs(hours) === 1 ? "hour" : "hours"}`;
  const relative = hours > 0 ? `${amount} ahead` : hours < 0 ? `${amount} behind` : "Same time";
  const day = local.dateKey < home.dateKey ? "Yesterday, " : local.dateKey > home.dateKey ? "Tomorrow, " : "";
  return { time, note: day ? `${day}${relative.charAt(0).toLowerCase()}${relative.slice(1)}` : relative };
}

/** The wall-clock reading of `date` in `timeZone`, and that zone's offset from UTC in minutes. */
function zonedParts(date: Date, timeZone: string) {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-US", {
      timeZone,
      hourCycle: "h23",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })
      .formatToParts(date)
      .map((part) => [part.type, part.value]),
  );
  const year = Number(parts.year);
  const month = Number(parts.month);
  const day = Number(parts.day);
  const hour = Number(parts.hour) % 24;
  const minute = Number(parts.minute);
  const asUtc = Date.UTC(year, month - 1, day, hour, minute);
  const wholeMinute = Math.floor(date.getTime() / 60_000) * 60_000;
  return {
    hour12: hour % 12 === 0 ? 12 : hour % 12,
    minute,
    dayPeriod: hour < 12 ? "am" : "pm",
    dateKey: year * 10_000 + month * 100 + day,
    offsetMinutes: Math.round((asUtc - wholeMinute) / 60_000),
  };
}
