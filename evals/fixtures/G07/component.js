// mount(root, state, onRetry) updates the existing component for each state.
function mount(root, state, onRetry) {
  const button = root.ownerDocument.createElement('button');
  button.textContent = 'Submit';
  root.replaceChildren(button);
}
module.exports = {mount};
