"use client";
import React from "react";
import Link from "next/link";
import WalletBar from "./WalletBar";
import { useRouter } from "next/router";

export default function Layout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const path = router.pathname || "";
  const showLogoBg = path === "/" || path.startsWith("/profile");

  return (
    <div className={`app${showLogoBg ? " bg-logo" : ""}`}>
      <header className="topbar">
        <div className="brand">
          <div className="logo">W</div>
          <div>
            <div className="brand-title">Wager Room</div>
            <div className="brand-sub">Powered by GenLayer</div>
          </div>
        </div>
        <nav className="nav">
          <Link href="/" className="nav-link">Lobby</Link>
          <Link href="/profile/me" className="nav-link">Profile</Link>
        </nav>
        <WalletBar />
      </header>
      <main className="main">{children}</main>
    </div>
  );
}
