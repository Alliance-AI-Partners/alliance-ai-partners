import Image, { type StaticImageData } from "next/image";
import advisoryDark from "@/design-system/icons/brand/advisory-dark.svg";
import advisoryMono from "@/design-system/icons/brand/advisory-mono.svg";
import aiStrategyDark from "@/design-system/icons/brand/ai-strategy-dark.svg";
import aiStrategyMono from "@/design-system/icons/brand/ai-strategy-mono.svg";
import automationDark from "@/design-system/icons/brand/automation-dark.svg";
import automationMono from "@/design-system/icons/brand/automation-mono.svg";
import cloudIntegrationDark from "@/design-system/icons/brand/cloud-integration-dark.svg";
import cloudIntegrationMono from "@/design-system/icons/brand/cloud-integration-mono.svg";
import dataAnalyticsDark from "@/design-system/icons/brand/data-analytics-dark.svg";
import dataAnalyticsMono from "@/design-system/icons/brand/data-analytics-mono.svg";
import growthDark from "@/design-system/icons/brand/growth-dark.svg";
import growthMono from "@/design-system/icons/brand/growth-mono.svg";
import launchDark from "@/design-system/icons/brand/launch-dark.svg";
import launchMono from "@/design-system/icons/brand/launch-mono.svg";
import machineLearningDark from "@/design-system/icons/brand/machine-learning-dark.svg";
import machineLearningMono from "@/design-system/icons/brand/machine-learning-mono.svg";
import partnershipDark from "@/design-system/icons/brand/partnership-dark.svg";
import partnershipMono from "@/design-system/icons/brand/partnership-mono.svg";
import researchInsightsDark from "@/design-system/icons/brand/research-insights-dark.svg";
import researchInsightsMono from "@/design-system/icons/brand/research-insights-mono.svg";
import securityGovernanceDark from "@/design-system/icons/brand/security-governance-dark.svg";
import securityGovernanceMono from "@/design-system/icons/brand/security-governance-mono.svg";
import trainingEnablementDark from "@/design-system/icons/brand/training-enablement-dark.svg";
import trainingEnablementMono from "@/design-system/icons/brand/training-enablement-mono.svg";
import { cn } from "@/lib/cn";

/**
 * The twelve service icons from the brand kit (design-system/icons/brand/), drawn on a 48px grid with a 2px stroke.
 * Mono is Partner Navy, for Daylight grounds; dark is white, for Partner Navy chapters (Figma: Service icon/Mono and
 * Service icon/Dark).
 */
const serviceIcons = {
  "advisory": { mono: advisoryMono, dark: advisoryDark },
  "ai-strategy": { mono: aiStrategyMono, dark: aiStrategyDark },
  "automation": { mono: automationMono, dark: automationDark },
  "cloud-integration": { mono: cloudIntegrationMono, dark: cloudIntegrationDark },
  "data-analytics": { mono: dataAnalyticsMono, dark: dataAnalyticsDark },
  "growth": { mono: growthMono, dark: growthDark },
  "launch": { mono: launchMono, dark: launchDark },
  "machine-learning": { mono: machineLearningMono, dark: machineLearningDark },
  "partnership": { mono: partnershipMono, dark: partnershipDark },
  "research-insights": { mono: researchInsightsMono, dark: researchInsightsDark },
  "security-governance": { mono: securityGovernanceMono, dark: securityGovernanceDark },
  "training-enablement": { mono: trainingEnablementMono, dark: trainingEnablementDark },
} satisfies Record<string, { mono: StaticImageData; dark: StaticImageData }>;

export type ServiceIconName = keyof typeof serviceIcons;

type ServiceIconProps = {
  name: ServiceIconName;
  /** mono on Daylight (the default), dark on Partner Navy. */
  tone?: "mono" | "dark";
  /** Size it here (`size-8 lg:size-10`); the icon is decorative, so the text beside it carries the meaning. */
  className?: string;
};

export function ServiceIcon({ name, tone = "mono", className }: ServiceIconProps) {
  return <Image src={serviceIcons[name][tone]} alt="" className={cn("shrink-0", className)} />;
}
