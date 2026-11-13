import PropTypes from 'prop-types';
import React from 'react';
import { sanitizeBidiText } from 'Utilities/String/isolateBidiText';

function sanitizeRenderedStrings(children, preserveBalancedIsolates) {
  if (typeof children === 'string') {
    return sanitizeBidiText(children, preserveBalancedIsolates);
  }

  if (Array.isArray(children)) {
    return children.map((child) => sanitizeRenderedStrings(child, preserveBalancedIsolates));
  }

  if (React.isValidElement(children) && children.props.children !== undefined) {
    return React.cloneElement(children, {}, sanitizeRenderedStrings(children.props.children, preserveBalancedIsolates));
  }

  return children;
}

function BidiText(props) {
  const { children, preserveBalancedIsolates, ...otherProps } = props;
  const safeProps = Object.fromEntries(Object.entries(otherProps).map(([name, value]) => {
    return [name, (name === 'title' || name.startsWith('aria-')) && typeof value === 'string' ?
      sanitizeBidiText(value) : value];
  }));

  return (
    <bdi dir="auto" {...safeProps}>
      {sanitizeRenderedStrings(children, preserveBalancedIsolates)}
    </bdi>
  );
}

BidiText.propTypes = {
  children: PropTypes.node.isRequired,
  preserveBalancedIsolates: PropTypes.bool
};

BidiText.defaultProps = {
  preserveBalancedIsolates: false
};

export default BidiText;
