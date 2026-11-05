import type { MetadataRoute } from "next";
import icon192 from "@/design-system/logos/app-icons/icon-192.png";
import icon512 from "@/design-system/logos/app-icons/icon-512.png";
import iconMaskable512 from "@/design-system/logos/app-icons/icon-maskable-512.png";

/** The web app manifest, from design-system/logos/app-icons/site.webmanifest with the icons served by the site. */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Alliance AI Partners",
    short_name: "Alliance AI",
    theme_color: "#121B2A",
    background_color: "#121B2A",
    display: "standalone",
    start_url: "/",
    icons: [
      { src: icon192.src, sizes: "192x192", type: "image/png" },
      { src: icon512.src, sizes: "512x512", type: "image/png" },
      { src: iconMaskable512.src, sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
