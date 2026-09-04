export default function LiveSystemFeed({ feed }) {
  return (
    <div className="card">
      <div className="card-title"><span className="emoji">📡</span> LIVE SYSTEM FEED</div>
      <div className="feed-list">
        {feed.length === 0 && <div className="feed-empty">Awaiting emergency trigger...</div>}
        {feed.map((item) => (
          <div className="feed-item" key={item.id}>
            <span className="feed-dot">●</span>
            <span className="feed-time">{item.time}</span>
            <span>{item.text}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
