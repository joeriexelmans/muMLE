export default function ThemeToggle() {
  const toggleTheme = () => {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');

    const next = current === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
  };

  return (
    <button className="theme-toggle" onClick={toggleTheme}>
      Toggle theme
    </button>
  );
}
