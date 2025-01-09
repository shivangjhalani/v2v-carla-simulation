import Dashboard from '../components/Dashboard'

export default function Home() {
  return (
    <>
      <style jsx global>{`
        .leaflet-container {
          height: 100%;
          width: 100%;
        }
      `}</style>
      <main className="min-h-screen bg-background">
        <Dashboard />
      </main>
    </>
  )
}

