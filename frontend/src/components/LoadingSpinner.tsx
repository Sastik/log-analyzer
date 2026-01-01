import React from 'react';
// import '../styles/components/LoadingSpinner.scss';
// import '../styles/components/

const LoadingSpinner: React.FC = () => {
  return (
    <div className="loading-spinner">
      <div className="spinner"></div>
      <p>Loading...</p>
    </div>
  );
};

export default LoadingSpinner;