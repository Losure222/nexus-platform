import React, { useState, useEffect } from 'react';

const SearchBar = ({ value, onChange, onSearch }) => {
  const [history, setHistory] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem("searchHistory")) || [];
    setHistory(stored);
  }, []);

  const handleSearch = () => {
    if (!value.trim()) return;

    const updated = [value.trim(), ...history.filter(h => h !== value.trim())].slice(0, 10);
    localStorage.setItem("searchHistory", JSON.stringify(updated));
    setHistory(updated);
    onSearch();
    setShowDropdown(false);
  };

  const handleSelect = (term) => {
    onChange({ target: { value: term } });
    setShowDropdown(false);
    setTimeout(() => onSearch(), 100); // Slight delay to let value update
  };

  return (
    <div className="search-bar" style={{ position: 'relative' }}>
      <input
        type="text"
        placeholder="Enter part number..."
        value={value}
        onChange={onChange}
        onFocus={() => setShowDropdown(true)}
        onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
        style={{ width: '250px' }}
      />
      <button onClick={handleSearch}>Search</button>

      {showDropdown && history.length > 0 && (
        <ul className="dropdown-history" style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          width: '250px',
          maxHeight: '150px',
          overflowY: 'auto',
          background: 'white',
          border: '1px solid #ccc',
          borderRadius: '4px',
          padding: 0,
          margin: 0,
          listStyle: 'none',
          zIndex: 10
        }}>
          {history.map((term, i) => (
            <li
              key={i}
              onMouseDown={() => handleSelect(term)}
              style={{
                padding: '6px 10px',
                cursor: 'pointer',
                borderBottom: '1px solid #eee'
              }}
            >
              {term}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default SearchBar;
