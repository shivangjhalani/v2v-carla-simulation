"use client"

import { useState } from "react"
import Link from "next/link"
import { MinusCircledIcon,Cross1Icon } from "@radix-ui/react-icons"

interface NavbarProps {
  links: { name: string; href: string }[]
  title?: string
}

export function Navbar({ links, title = "Dashboard" }: NavbarProps) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <nav className="bg-muted/10 border-b p-4">
      <div className="flex items-center justify-between">
        {/* Logo and Title */}
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden p-2 border rounded"
          >
            {isOpen ? (
              <Cross1Icon className="h-5 w-5 text-muted-foreground" />
            ) : (
              <MinusCircledIcon className="h-5 w-5 text-muted-foreground" />
            )}
          </button>
          <span className="text-xl font-bold">{title}</span>
        </div>

        {/* Navigation Links (Desktop) */}
        <div className="hidden md:flex space-x-6">
          {links.map((link, index) => (
            <Link
              key={index}
              href={link.href}
              className="text-muted-foreground hover:text-foreground"
            >
              {link.name}
            </Link>
          ))}
        </div>
      </div>

      {/* Mobile Navigation Menu */}
      {isOpen && (
        <div className="md:hidden mt-4 space-y-2">
          {links.map((link, index) => (
            <Link
              key={index}
              href={link.href}
              className="block text-muted-foreground hover:text-foreground"
              onClick={() => setIsOpen(false)}
            >
              {link.name}
            </Link>
          ))}
        </div>
      )}
    </nav>
  )
}
