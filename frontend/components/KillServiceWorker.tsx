"use client";

import { useEffect } from "react";

export default function KillServiceWorker() {
  useEffect(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.getRegistrations().then((registrations) => {
        for (let registration of registrations) {
          registration.unregister();
          console.log("Unregistered SW:", registration);
        }
      });
    }
  }, []);

  return null;
}
