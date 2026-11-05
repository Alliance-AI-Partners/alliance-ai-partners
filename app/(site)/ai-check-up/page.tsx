import { Booked } from "@/components/ai-check-up/booked";
import { Booking } from "@/components/ai-check-up/booking";
import { Hero } from "@/components/ai-check-up/hero";
import { Questions } from "@/components/ai-check-up/questions";
import { WhatWeLookAt } from "@/components/ai-check-up/what-we-look-at";
import { WhatYouGet } from "@/components/ai-check-up/what-you-get";
import { WhoItIsFor } from "@/components/ai-check-up/who-it-is-for";
import { FormFlow } from "@/components/blocks/form-flow";
import { pageMetadata } from "@/lib/metadata";

export const metadata = pageMetadata({
  title: "The AI check-up | Alliance AI Partners",
  description:
    "Our usual first project, at a fixed price. In [two weeks] we find where AI could save your team time or money, and hand you a written plan with a fixed quote for the first fix. From [PRICE].",
  path: "/ai-check-up",
});

/**
 * AI check-up (Figma: 02 · AI check-up, frames AI check-up — Desktop 39:528 and — Mobile 43:740, plus the Booked
 * frames 43:5529 and 43:5718; record: docs/website/pages/ai-check-up.json). Sending the booking form swaps the page
 * for the Booked view.
 */
export default function AiCheckUpPage() {
  return (
    <FormFlow done={<Booked />}>
      <Hero />
      <WhatWeLookAt />
      <WhatYouGet />
      <WhoItIsFor />
      <Booking />
      <Questions />
    </FormFlow>
  );
}
