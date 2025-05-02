import React, { useState } from 'react';
import { Box, Button, TextField, Typography, Paper, Link, Container } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { supabase } from './supabaseClient';

export default function SignUp() {
  const [name, setName] = useState('');
  const [surname, setSurname] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [verifyPassword, setVerifyPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError('');
    if (password !== verifyPassword) {
      setError('Passwords do not match.');
      return;
    }
    setLoading(true);
    // Supabase Auth sign up
    const { data, error: signUpError } = await supabase.auth.signUp({ email, password });
    if (signUpError) {
      setError(signUpError.message);
      setLoading(false);
      return;
    }
    // Insert profile info
    const user = data.user;
    if (user) {
      await supabase.from('profiles').upsert({ id: user.id, name, surname, phone });
      setLoading(false);
      navigate('/dashboard');
    } else {
      setError('Sign up failed. Please check your email for confirmation.');
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="xs" sx={{ mt: 8 }}>
      <Paper sx={{ p: 4, borderRadius: 3 }}>
        <Typography variant="h5" align="center" gutterBottom>Sign Up for One</Typography>
        <form onSubmit={handleSignUp}>
          <TextField label="Name" fullWidth margin="normal" value={name} onChange={e => setName(e.target.value)} />
          <TextField label="Surname" fullWidth margin="normal" value={surname} onChange={e => setSurname(e.target.value)} />
          <TextField label="Email" fullWidth margin="normal" value={email} onChange={e => setEmail(e.target.value)} />
          <TextField label="Phone Number" fullWidth margin="normal" value={phone} onChange={e => setPhone(e.target.value)} />
          <TextField label="Password" type="password" fullWidth margin="normal" value={password} onChange={e => setPassword(e.target.value)} />
          <TextField label="Verify Password" type="password" fullWidth margin="normal" value={verifyPassword} onChange={e => setVerifyPassword(e.target.value)} />
          {error && <Typography color="error" sx={{ mt: 1 }}>{error}</Typography>}
          <Button type="submit" variant="contained" color="primary" fullWidth sx={{ mt: 2 }} disabled={loading}>{loading ? 'Signing Up...' : 'Sign Up'}</Button>
        </form>
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Link component="button" variant="body2" onClick={() => navigate('/login')}>Already have an account? Login</Link>
        </Box>
      </Paper>
    </Container>
  );
} 