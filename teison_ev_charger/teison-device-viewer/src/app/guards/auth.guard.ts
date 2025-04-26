import {CanActivateFn, Router} from '@angular/router';
import {inject} from "@angular/core";

export const authGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);  // Use Angular's DI to inject the Router service

  // Check if the token is available in localStorage (or sessionStorage)
  const token = localStorage.getItem('token_key');

  if (token) {
    return true;  // Allow access to the route if the token exists
  } else {
    router.navigate(['/login']);  // Redirect to login if no token is found
    return false;  // Deny access to the route
  }
};
