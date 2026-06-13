interface MissingDataPillsProps {
  missing: string[];
}

export default function MissingDataPills({ missing }: MissingDataPillsProps) {
  if (missing.length === 0) {
    return null;
  }

  return (
    <div className="app-missing">
      <p className="app-missing__label">Missing information</p>
      <div className="app-missing__row">
        {missing.map((item) => (
          <span key={item} className="app-missing__pill">
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
