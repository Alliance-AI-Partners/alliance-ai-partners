/*
 * Where the site's forms send what people type in them (AI check-up booking, contact, newsletter, talent list, job
 * applications). No service is connected yet: that is a decision for Alliance AI Partners (for example an email
 * service, a CRM form or a booking tool). Until one is connected, nothing a visitor types leaves their browser.
 *
 * - On your computer and on Vercel preview deployments, a form that passes its checks shows the designed
 *   confirmation (the Figma "· Booked" and "· Sent" frames), so the whole flow can be reviewed. It sends nothing.
 * - On the production site, a form says that online sending is not open yet and offers the email address instead,
 *   so no visitor believes a message was sent when it was not.
 *
 * To connect a service: send the data in `submitForm` below (for example to a route handler or server action that
 * calls the service), set `formsConnected` to true, and update the privacy policy with the new processor.
 *
 * Whether a form runs in demo mode is decided on the server, in lib/forms-mode.ts, and passed to the form as a prop.
 */

/** True once `submitForm` really delivers what a visitor sends. */
export const formsConnected = false;

export type FormResult = "sent" | "not-connected";

/**
 * Send one form. Resolves "sent" once the data is delivered (or, in demo mode, after a short pause so the busy state
 * shows), or "not-connected" when there is nowhere to send it.
 */
export async function submitForm(form: string, data: Record<string, string>, demo: boolean): Promise<FormResult> {
  void form;
  void data;
  if (formsConnected) {
    // Connect the chosen service here, then return "sent" on success and throw on failure.
    return "sent";
  }
  if (demo) {
    await new Promise((resolve) => setTimeout(resolve, 600));
    return "sent";
  }
  return "not-connected";
}
