import { createClient } from '@supabase/supabase-js';

// TODO: Replace with your own values from Supabase project settings
const supabaseUrl = 'https://xqyhrcznzkwkvgfcuebp.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhxeWhyY3puemt3a3ZnZmN1ZWJwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU4NTQzMzEsImV4cCI6MjA2MTQzMDMzMX0.k5yv2CCQDnlqv-QnGd-C4qGlPEWyWoysC5mgov4US_Q';

export const supabase = createClient(supabaseUrl, supabaseAnonKey); 