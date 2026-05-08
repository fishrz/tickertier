import { useParams } from 'react-router-dom'

function Stub({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-32 text-center">
      <div className="text-6xl mb-6">🚧</div>
      <h2 className="zh text-text">{title}</h2>
      {sub ? <div className="text-muted mt-3 zh">{sub}</div> : null}
      <div className="text-muted mt-2 zh">建设中</div>
    </div>
  )
}

export function StockDetail() {
  const { ticker } = useParams()
  return <Stub title="个股详情" sub={ticker ? `代码 ${ticker}` : undefined} />
}

export function HallOfFame() {
  return <Stub title="名人堂" />
}

export function Race() {
  return <Stub title="Race 赛道" />
}

export function Portfolio() {
  return <Stub title="持仓" />
}
