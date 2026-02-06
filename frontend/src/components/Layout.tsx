"use client";
import React from "react";
import Link from "next/link";
import WalletBar from "./WalletBar";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="logo">W</div>
          <div>
            <div className="brand-title">Wager Room</div>
            <div className="brand-sub">GenLayer predictions</div>
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
