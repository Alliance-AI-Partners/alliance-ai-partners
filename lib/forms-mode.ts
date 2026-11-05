import { formsConnected } from "@/lib/forms";

/**
 * Show a form's confirmation without sending anything (see lib/forms.ts): everywhere except the production site,
 * until a service is connected. Import this only in server components and pass it to the form as a `demo` prop:
 * VERCEL_ENV is a server-side variable, so the browser would always read it as unset.
 */
export const formsDemo = !formsConnected && process.env.VERCEL_ENV !== "production";
