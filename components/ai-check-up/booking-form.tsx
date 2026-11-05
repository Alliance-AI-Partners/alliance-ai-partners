"use client";

import { useRef, useState, type FormEvent } from "react";
import Link from "@/components/site-link";
import { Alert } from "@/components/blocks/alert";
import { Checkbox, FieldMessage, RadioOption, SelectField, TextField, TextareaField } from "@/components/blocks/form-fields";
import { useFormFlowDone } from "@/components/blocks/form-flow";
import { Icon } from "@/components/icon";
import { submitForm } from "@/lib/forms";
import { contactEmail } from "@/lib/site";

/*
 * Where the visitor's team works, and the time zone the call times are shown in. The list covers the three markets;
 * "Somewhere else" uses the browser's own time zone. Figma shows the form filled in for New York.
 */
const zones = [
  { value: "us-eastern", label: "United States · Eastern Time", tz: "America/New_York", city: "New York", locale: "en-US" },
  { value: "us-central", label: "United States · Central Time", tz: "America/Chicago", city: "Chicago", locale: "en-US" },
  { value: "us-mountain", label: "United States · Mountain Time", tz: "America/Denver", city: "Denver", locale: "en-US" },
  { value: "us-pacific", label: "United States · Pacific Time", tz: "America/Los_Angeles", city: "Los Angeles", locale: "en-US" },
  { value: "uk", label: "United Kingdom", tz: "Europe/London", city: "London", locale: "en-GB" },
  { value: "au-eastern", label: "Australia · Sydney, Melbourne, Canberra", tz: "Australia/Sydney", city: "Sydney", locale: "en-AU" },
  { value: "au-queensland", label: "Australia · Brisbane", tz: "Australia/Brisbane", city: "Brisbane", locale: "en-AU" },
  { value: "au-western", label: "Australia · Perth", tz: "Australia/Perth", city: "Perth", locale: "en-AU" },
  { value: "elsewhere", label: "Somewhere else", tz: "", city: "", locale: "en-US" },
] as const;

/*
 * The sample call times (Figma: Radio group · First call, tagged "Sample times"): fixed moments until a booking tool is
 * connected. The labels as first served are Figma's, for New York; choosing another place reworks them in the browser.
 */
const slots = [
  { id: "slot-1", utc: Date.UTC(2026, 10, 17, 22), label: "Tuesday, November 17, 5:00 pm EST", manila: "6:00 am Wednesday in Manila" },
  { id: "slot-2", utc: Date.UTC(2026, 10, 18, 22), label: "Wednesday, November 18, 5:00 pm EST", manila: "6:00 am Thursday in Manila" },
  { id: "slot-3", utc: Date.UTC(2026, 10, 20, 0), label: "Thursday, November 19, 7:00 pm EST", manila: "8:00 am Friday in Manila" },
];

type Zone = { tz: string; city: string; locale: string };

/** "Tuesday, November 17, 5:00 pm EST" for one moment in one time zone. */
function slotLabel(utc: number, zone: Zone) {
  const parts = new Intl.DateTimeFormat(zone.locale, {
    timeZone: zone.tz,
    weekday: "long",
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hourCycle: "h12",
    timeZoneName: "short",
  }).formatToParts(new Date(utc));
  const get = (type: Intl.DateTimeFormatPartTypes) => parts.find((part) => part.type === type)?.value ?? "";
  return `${get("weekday")}, ${get("month")} ${get("day")}, ${get("hour")}:${get("minute")} ${get("dayPeriod").toLowerCase()} ${get("timeZoneName")}`;
}

/** The time zone's short name at the first sample time, for the caption: "EST", "GMT", "AEDT". */
function zoneName(zone: Zone) {
  return (
    new Intl.DateTimeFormat(zone.locale, { timeZone: zone.tz, timeZoneName: "short" })
      .formatToParts(new Date(slots[0].utc))
      .find((part) => part.type === "timeZoneName")?.value ?? ""
  );
}

function resolveZone(value: string): Zone {
  const zone = zones.find((item) => item.value === value) ?? zones[0];
  if (zone.value !== "elsewhere") return zone;
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
  return { tz, city: tz.split("/").pop()?.replace(/_/g, " ") ?? tz, locale: "en-US" };
}

type Errors = Partial<Record<"name" | "email" | "company" | "zone" | "slowdown" | "time" | "consent", string>>;

function validate(data: FormData): Errors {
  const value = (key: string) => String(data.get(key) ?? "").trim();
  const errors: Errors = {};
  if (!value("name")) errors.name = "Add your name.";
  const email = value("email");
  if (!email) errors.email = "Add your work email, so we can reply.";
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = "Add the domain, for example ops@company.com, so we can reply.";
  if (!value("company")) errors.company = "Add your company’s name.";
  if (!value("zone")) errors.zone = "Choose where your team works.";
  if (value("slowdown").length < 10) errors.slowdown = "Tell us a little more so we can prepare.";
  if (!value("time")) errors.time = "Pick a time, or ask us to email other times.";
  if (!data.get("consent")) errors.consent = "Tick the box so we can use these details to arrange your check-up.";
  return errors;
}

/** The order the fields appear in, to move focus to the first one that needs attention. */
const fieldOrder: (keyof Errors)[] = ["name", "email", "company", "zone", "slowdown", "time", "consent"];

/**
 * The AI check-up booking form (Figma: Section · Booking form › Form). Two fields to a row from 1024px, one on phones.
 * It checks itself before sending; until a booking service is connected it sends nothing (lib/forms.ts): in demo
 * mode it shows the Booked view, and on the production site it offers the email address instead.
 */
export function BookingForm({ demo }: { demo: boolean }) {
  const done = useFormFlowDone();
  const form = useRef<HTMLFormElement>(null);
  const [errors, setErrors] = useState<Errors>({});
  const [busy, setBusy] = useState(false);
  const [closed, setClosed] = useState(false);
  const [zoneValue, setZoneValue] = useState<string>(zones[0].value);

  const zone = zoneValue === zones[0].value ? null : resolveZone(zoneValue);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const data = new FormData(event.currentTarget);
    const found = validate(data);
    setErrors(found);
    const first = fieldOrder.find((key) => found[key]);
    if (first) {
      form.current?.querySelector<HTMLElement>(`[data-field="${first}"]`)?.focus();
      return;
    }
    setBusy(true);
    const result = await submitForm("ai-check-up", Object.fromEntries([...data].map(([k, v]) => [k, String(v)])), demo);
    setBusy(false);
    if (result === "sent") done?.();
    else setClosed(true);
  }

  return (
    <form
      ref={form}
      noValidate
      onSubmit={onSubmit}
      onChange={(event) => {
        // A field's error goes as soon as the visitor changes that field.
        const name = (event.target as unknown as HTMLInputElement).name as keyof Errors;
        if (errors[name]) setErrors((current) => ({ ...current, [name]: undefined }));
      }}
      aria-label="Book your AI check-up"
      className="aap-card grid items-start gap-5 p-5 lg:grid-cols-2 lg:gap-6 lg:p-10"
    >
      <TextField id="booking-name" data-field="name" name="name" label="Name" placeholder="Your full name" autoComplete="name" error={errors.name} />
      <TextField
        id="booking-email"
        data-field="email"
        name="email"
        type="email"
        label="Work email"
        placeholder="name@company.example"
        autoComplete="email"
        help="We send the confirmation here."
        error={errors.email}
      />
      <TextField
        id="booking-company"
        data-field="company"
        name="company"
        label="Company"
        placeholder="Company name"
        autoComplete="organization"
        error={errors.company}
      />
      <TextField
        id="booking-website"
        name="website"
        label="Website (optional)"
        placeholder="company.example"
        inputMode="url"
        autoComplete="url"
      />
      <SelectField
        id="booking-zone"
        data-field="zone"
        name="zone"
        label="Where your team is"
        help="We show call times in your time zone."
        error={errors.zone}
        className="lg:col-span-2"
        value={zoneValue}
        onChange={(event) => setZoneValue(event.target.value)}
      >
        {zones.map((item) => (
          <option key={item.value} value={item.value}>
            {item.label}
          </option>
        ))}
      </SelectField>
      <TextareaField
        id="booking-slowdown"
        data-field="slowdown"
        name="slowdown"
        label="What slows your team down?"
        placeholder="For example: we type every order from email into our system by hand."
        help="A few sentences is plenty."
        error={errors.slowdown}
        className="lg:col-span-2"
      />

      <div
        role="radiogroup"
        aria-labelledby="booking-time-label"
        aria-describedby={errors.time ? "booking-time-help booking-time-error" : "booking-time-help"}
        className="flex flex-col gap-2 lg:col-span-2 lg:gap-3"
      >
        <div className="flex items-center justify-between gap-3">
          <span id="booking-time-label" className="aap-label">
            Pick a time for the first call
          </span>
          <span className="aap-tag shrink-0">Sample times</span>
        </div>
        <ul className="border-t border-line">
          {slots.map((slot, index) => (
            <li
              key={slot.id}
              className="flex flex-col gap-1 border-b border-line py-3 lg:flex-row lg:items-center lg:gap-4 lg:py-3.5"
            >
              <RadioOption
                id={`booking-${slot.id}`}
                data-field={index === 0 ? "time" : undefined}
                name="time"
                value={slot.id}
                label={zone ? slotLabel(slot.utc, zone) : slot.label}
                className="lg:flex-1"
              />
              <span className="aap-mono pl-7 text-ink-secondary lg:pl-0">{slot.manila}</span>
            </li>
          ))}
          <li className="flex border-b border-line py-3 lg:py-3.5">
            <RadioOption id="booking-slot-other" name="time" value="other" label="None of these. Email me other times." />
          </li>
        </ul>
        <p id="booking-time-help" className="text-caption text-ink-secondary">
          Shown in your time zone, {zone ? `${zone.city} (${zoneName(zone)})` : "New York (EST)"}, with our time in
          Manila.
        </p>
        <FieldMessage id="booking-time" error={errors.time} />
      </div>

      <Checkbox id="booking-consent" data-field="consent" name="consent" error={errors.consent} className="lg:col-span-2">
        I agree that Alliance AI Partners may use these details to arrange my AI check-up, as set out in the{" "}
        <Link href="/privacy">privacy policy</Link>.
      </Checkbox>

      <div className="flex flex-col gap-5 lg:col-span-2 lg:gap-3 lg:pt-2">
        <button
          type="submit"
          className="aap-button aap-button--primary aap-button--lg w-full lg:w-auto lg:self-start"
          aria-busy={busy || undefined}
        >
          Book your AI check-up
          <Icon name="arrow-right" />
        </button>
        <p className="text-caption text-ink-secondary">You agree the fixed price before any work starts.</p>
      </div>

      {closed ? (
        <Alert type="info" role="status" title="Online booking isn’t open yet." className="lg:col-span-2">
          Email <a href={`mailto:${contactEmail}`}>{contactEmail}</a> and we’ll find a time for your first call.
        </Alert>
      ) : null}
    </form>
  );
}
