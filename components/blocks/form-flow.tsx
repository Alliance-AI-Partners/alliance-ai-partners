"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";

/**
 * A page whose form, once sent, is replaced by a confirmation view (Figma: the "· Booked" and "· Sent" frames).
 * The page's sections stay server-rendered: they come in as `children`, the confirmation as `done`. A form inside
 * calls `useFormFlowDone()` when it has been sent; the flow swaps the views, scrolls to the top and moves focus to
 * the element in `done` marked `data-form-flow-focus` (give it tabIndex={-1}), so screen readers announce it.
 */
const FormFlowContext = createContext<(() => void) | null>(null);

export function FormFlow({ children, done }: { children: ReactNode; done: ReactNode }) {
  const [isDone, setDone] = useState(false);
  const wrapper = useRef<HTMLDivElement>(null);

  const finish = useCallback(() => setDone(true), []);

  useEffect(() => {
    if (!isDone) return;
    window.scrollTo({ top: 0 });
    wrapper.current?.querySelector<HTMLElement>("[data-form-flow-focus]")?.focus({ preventScroll: true });
  }, [isDone]);

  return (
    <FormFlowContext value={finish}>
      <div ref={wrapper} className="contents">
        {isDone ? done : children}
      </div>
    </FormFlowContext>
  );
}

/** The function a form calls once it has been sent. Null outside a FormFlow. */
export function useFormFlowDone() {
  return useContext(FormFlowContext);
}
