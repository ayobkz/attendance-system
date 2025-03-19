// !!! ВАЖНО: ИЗМЕНИТЕ URL НА АКТУАЛЬНЫЙ IP-АДРЕС ВАШЕГО СЕРВЕРА !!!
const handleLogout = async () => {
  try {
    const response = await fetch('http://192.168.8.21:8000/api/logout/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    } else {
      console.error('Ошибка при выходе из системы');
    }
  } catch (error) {
    console.error('Ошибка при выполнении запроса:', error);
  }
}; 