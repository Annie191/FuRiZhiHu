export default function PageHeader({ eyebrow, title, actions }) {
  return (
    <section className="page-title-row">
      <div>
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
      </div>
      {actions ? <div className="toolbar-actions">{actions}</div> : null}
    </section>
  );
}
