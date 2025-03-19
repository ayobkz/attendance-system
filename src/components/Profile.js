return (
  <div className="profile">
    <h2>Профиль</h2>
    {userProfile ? (
      <>
        <p>Имя: {userProfile.name || 'Не указано'}</p>
        <p>Email: {userProfile.email || 'Не указано'}</p>
        <p>Телефон: {userProfile.phone || 'Не указан'}</p>
        {/* Другие поля профиля */}
      </>
    ) : (
      <p>Профиль не заполнен</p>
    )}
  </div>
); 