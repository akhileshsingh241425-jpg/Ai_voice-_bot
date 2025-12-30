declare module 'react-router-bootstrap' {
  import { ComponentType } from 'react';
  import { NavLinkProps } from 'react-bootstrap';

  export interface LinkContainerProps {
    to: string;
    children: React.ReactNode;
    className?: string;
    activeClassName?: string;
    exact?: boolean;
  }

  export const LinkContainer: ComponentType<LinkContainerProps>;
}