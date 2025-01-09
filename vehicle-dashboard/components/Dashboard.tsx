import TopPanel from './TopPanel'
import LeftPanel from './LeftPanel'
import CenterPanel from './CenterPanel'
import RightPanel from './RightPanel'

export default function Dashboard() {
  return (
    <div className="flex flex-col h-screen">
      <TopPanel />
      <div className="flex flex-1 overflow-hidden">
        <LeftPanel />
        <CenterPanel />
        <RightPanel />
      </div>
    </div>
  )
}

