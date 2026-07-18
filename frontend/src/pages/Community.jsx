import { Heart, MessageSquareText, RefreshCw } from 'lucide-react';
import { useEffect, useState } from 'react';

import { getCommunityPosts } from '../api/fucareApi.js';
import PageHeader from '../components/PageHeader.jsx';
import StatCard from '../components/StatCard.jsx';
import StateBlock from '../components/StateBlock.jsx';

export default function Community() {
  const [limit, setLimit] = useState(20);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function loadPosts() {
    setLoading(true);
    setError('');
    getCommunityPosts(limit)
      .then(setPosts)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadPosts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [limit]);

  const totalLikes = posts.reduce((sum, item) => sum + item.likesCount, 0);
  const topPost = posts.reduce((top, item) => (item.likesCount > (top?.likesCount || 0) ? item : top), null);

  return (
    <section className="wide-page">
      <PageHeader
        eyebrow="Community"
        title="社区动态"
        actions={
          <>
            <label>
              <span>数量</span>
              <select value={limit} onChange={(event) => setLimit(Number(event.target.value))}>
                <option value={10}>10 条</option>
                <option value={20}>20 条</option>
                <option value={50}>50 条</option>
              </select>
            </label>
            <button className="icon-button" type="button" onClick={loadPosts} aria-label="刷新社区">
              <RefreshCw size={18} />
            </button>
          </>
        }
      />

      <StateBlock loading={loading} error={error} empty={!posts.length}>
        <div className="stat-grid">
          <StatCard label="公开动态" value={`${posts.length}条`} hint="按发布时间倒序" tone="teal" />
          <StatCard label="总点赞" value={totalLikes} hint="来自数据库 likes_count" tone="coral" />
          <StatCard label="最高点赞" value={topPost?.likesCount || 0} hint={topPost?.author || '-'} tone="violet" />
        </div>

        <div className="post-list">
          {posts.map((post) => (
            <article className="post-row" key={post.id}>
              <div className="post-avatar">
                <MessageSquareText size={20} />
              </div>
              <div className="post-body">
                <div className="post-meta">
                  <strong>{post.author}</strong>
                  <span>{post.postedAt}</span>
                </div>
                <p>{post.content}</p>
                <span className="like-count">
                  <Heart size={15} />
                  {post.likesCount}
                </span>
              </div>
            </article>
          ))}
        </div>
      </StateBlock>
    </section>
  );
}
