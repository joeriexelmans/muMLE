import { useCallback } from 'react';

export const useDatatypes = (setDatatypes) => {
  const add = useCallback(() => setDatatypes(prev => [...prev, { name: '' }]), [setDatatypes]);
  const remove = useCallback(index => setDatatypes(prev => prev.filter((_, i) => i !== index)), [setDatatypes]);
  const update = useCallback((index, value) => setDatatypes(prev => prev.map((dt, i) => i === index ? { ...dt, name: value } : dt)), [setDatatypes]);
  const moveUp = useCallback(index => setDatatypes(prev => {
    if (index === 0) return prev;
    const arr = [...prev];
    [arr[index-1], arr[index]] = [arr[index], arr[index-1]];
    return arr;
  }), [setDatatypes]);
  const moveDown = useCallback(index => setDatatypes(prev => {
    if (index === prev.length-1) return prev;
    const arr = [...prev];
    [arr[index+1], arr[index]] = [arr[index], arr[index+1]];
    return arr;
  }), [setDatatypes]);

  return { add, remove, update, moveUp, moveDown };
};
