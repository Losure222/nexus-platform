import React, { useState } from 'react';
import './App.css';
import SearchBar from './SearchBar';
import ResultsGrid from './ResultsGrid';

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [csvResults, setCsvResults] = useState([]);
  const [ebayResults, setEbayResults] = useState([]);

  const [filterCondition, setFilterCondition] = useState([]);
  const [filterCountry, setFilterCountry] = useState([]);
  // Default supplier filter set to both "vendor" and "ebay"
  const [filterType, setFilterType] = useState(["vendor", "ebay"]);
  const [sortByPrice, setSortByPrice] = useState(false);

  const COUNTRY_MAP = {
    usa: ['us', 'usa', 'united states', 'united states of america'],
    europe: ['de', 'fr', 'it', 'nl', 'pl', 'es', 'eu', 'europe'],
    china: ['cn', 'china']
  };

  const toggleFilter = (value, setter) => {
    setter(prev =>
      prev.includes(value) ? prev.filter(v => v !== value) : [...prev, value]
    );
  };

  const handleSearch = async () => {
    if (!searchTerm) return;

    try {
      const res = await fetch(`https://nexus-backend-6xfb.onrender.com/parts?query=${searchTerm}`);
      const data = await res.json();

      setCsvResults(data.csv_results || []);
      setEbayResults(data.ebay_results || []);
    } catch (error) {
      console.error("API fetch failed:", error);
    }
  };

  const filterByConditionAndCountry = (item) => {
    const conditionText = item.condition?.toLowerCase() || '';
    const itemCountry =
      item.country?.toLowerCase() ||
      item.itemLocation?.country?.toLowerCase() || '';
    const itemType = item.type?.toLowerCase() || '';

    const conditionMatch =
      filterCondition.length === 0 ||
      filterCondition.some(cond => conditionText.includes(cond));

    const countryMatch =
      filterCountry.length === 0 ||
      filterCountry.some(filter => COUNTRY_MAP[filter]?.includes(itemCountry));

    const typeMatch =
      filterType.length === 0 || filterType.includes(itemType);

    return conditionMatch && countryMatch && typeMatch;
  };

  const sortByLowestPrice = (results) => {
    return [...results].sort((a, b) => {
      const aPrice = typeof a.price === 'object' ? parseFloat(a.price?.value) : parseFloat(a.price);
      const bPrice = typeof b.price === 'object' ? parseFloat(b.price?.value) : parseFloat(b.price);
      return aPrice - bPrice;
    });
  };

  const combinedResults = [...csvResults, ...ebayResults].filter(filterByConditionAndCountry);
  const sortedResults = sortByPrice ? sortByLowestPrice(combinedResults) : combinedResults;

  return (
    <div className="app">
      {/* Top Header */}
      <header className="app-header">
        <div className="header-left">
          <span className="nexus-title">Nexus</span>
        </div>
        <div className="header-center">
          <img src="/stanlo-logo.png" alt="Stanlo Automation" className="stanlo-logo" />
        </div>
        <div className="header-right" />
      </header>

      {/* Main Layout */}
      <div
        className="layout"
        style={{
          backgroundImage: "url('/background.webp')",
          backgroundSize: 'cover',
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed'
        }}
      >
        <aside className="sidebar">
          <SearchBar
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            onSearch={handleSearch}
          />

          <button
            style={{
              margin: '1rem 0',
              padding: '8px 12px',
              background: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              width: '100%'
            }}
            onClick={() => setSortByPrice(!sortByPrice)}
          >
            {sortByPrice ? 'Default Order' : 'Sort by Lowest Price'}
          </button>

          <h4>Condition</h4>
          {["New", "Used", "Refurbished", "Service Exchange"].map(cond => (
            <label key={cond}>
              <input
                type="checkbox"
                checked={filterCondition.includes(cond.toLowerCase())}
                onChange={() => toggleFilter(cond.toLowerCase(), setFilterCondition)}
              />
              {cond}
            </label>
          ))}

          <h4 style={{ marginTop: '1rem' }}>Country</h4>
          {["usa", "europe", "china"].map(cty => (
            <label key={cty}>
              <input
                type="checkbox"
                checked={filterCountry.includes(cty)}
                onChange={() => toggleFilter(cty, setFilterCountry)}
              />
              {cty.charAt(0).toUpperCase() + cty.slice(1)}
            </label>
          ))}

          <h4 style={{ marginTop: '1rem' }}>Supplier Type</h4>
          <label>
            <input
              type="checkbox"
              checked={filterType.includes("vendor")}
              onChange={() => toggleFilter("vendor", setFilterType)}
            />
            Trusted Suppliers
          </label>
          <label>
            <input
              type="checkbox"
              checked={filterType.includes("ebay")}
              onChange={() => toggleFilter("ebay", setFilterType)}
            />
            eBay Suppliers
          </label>
        </aside>

        <main
          className="results-section"
          style={{
            backgroundImage: "url('/background.webp')",
            backgroundSize: 'cover',
            backgroundRepeat: 'no-repeat',
            backgroundPosition: 'center',
            backgroundAttachment: 'fixed',
            padding: '2rem',
            borderRadius: '12px'
          }}
        >
          <div className="results-container">
            <ResultsGrid results={sortedResults} />
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
