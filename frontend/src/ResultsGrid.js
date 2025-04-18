import React from 'react';

const ResultsGrid = ({ results = [] }) => {
  if (!results || results.length === 0) {
    return <div className="no-results">No results found. Try a different search.</div>;
  }

  return (
    <div className="results-container">
      {results.map((item, index) => {
        const isEbay = !!item.itemWebUrl;

        const conditionClass = item.condition
          ? `condition ${item.condition.toLowerCase().replace(/\s+/g, "-")}`
          : "condition";

        const imageUrl =
          item.image?.imageUrl ||
          item.image?.url ||
          item.thumbnailImages?.[0]?.imageUrl ||
          'https://via.placeholder.com/150'; // Fallback image if none exists

        const location = item.country || item.itemLocation?.country || item.location || 'N/A';
        const quantity = item.quantity && item.quantity !== '0' ? item.quantity : 'N/A'; // Default to 'N/A' if no quantity available

        const displayPrice = (() => {
          const rawPrice = typeof item.price === 'object' ? item.price?.value : item.price;
          const parsed = parseFloat(rawPrice);
          return isNaN(parsed) ? 'N/A' : `$${parsed.toFixed(2)}`;
        })();

        return (
          <div key={index} className="result-card" style={{ position: 'relative', padding: '16px', borderRadius: '12px', background: '#fff', boxShadow: '0 2px 10px rgba(0,0,0,0.05)', marginBottom: '20px' }}>
            {/* Quantity in Top Right */}
            {quantity !== 'N/A' && (
              <div style={{ position: 'absolute', top: '12px', right: '12px', background: '#3DBCDB', color: 'white', padding: '4px 8px', borderRadius: '12px', fontSize: '12px' }}>
                {quantity} in stock
              </div>
            )}

            {imageUrl && (
              <img
                src={imageUrl}
                alt={item.title || item.part_number}
                style={{
                  maxWidth: "100%",
                  height: "150px",
                  objectFit: "contain",
                  marginBottom: "0.5rem",
                  borderRadius: "8px"
                }}
              />
            )}

            <p><strong>{isEbay ? item.title : item.part_number}</strong></p>
            {item.condition && (
              <p><span className={conditionClass}>{item.condition}</span></p>
            )}
            <p>Price: {displayPrice}</p>

            {isEbay ? (
              <>
                <p>Seller: {item.seller?.username || 'Unknown'}</p>
                <p>Location: {location}</p>
                <a href={item.itemWebUrl} target="_blank" rel="noopener noreferrer">
                  View on eBay
                </a>
              </>
            ) : (
              <>
                <p>Lead Time: {item.lead_time || 'N/A'}</p> {/* Ensure 'lead_time' is properly checked */}
                <p>Vendor: {item.vendor || 'N/A'}</p> {/* Handle missing vendor field */}
                <p>Location: {location}</p>
              </>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default ResultsGrid;
