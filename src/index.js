"use strict";

var _react = _interopRequireDefault(require("react"));
var _reactDom = _interopRequireDefault(require("react-dom"));
var _App = _interopRequireDefault(require("./App"));
// import './index.css';
// require('./index.css');
function _interopRequireDefault(e) { return e && e.__esModule ? e : { "default": e }; }
// Ensure this path matches your App.js location
// Optional: If you have a CSS file for styles

_reactDom["default"].render(/*#__PURE__*/_react["default"].createElement(_react["default"].StrictMode, null, /*#__PURE__*/_react["default"].createElement(_App["default"], null)), document.getElementById('root'));
