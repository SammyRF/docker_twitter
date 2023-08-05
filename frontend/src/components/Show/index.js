import PropTypes from 'prop-types';

const Show = ({ visible, children }) => (
  <div style={{ display: visible ? 'block' : 'none' }}>
    {visible && children}
  </div>
);

Show.propTypes = {
  visible: PropTypes.bool.isRequired,
  children: PropTypes.node.isRequired,
};

export default Show;
